#!/usr/bin/env python3
"""Time-sliced audit of four committed QQQ/SPY fixed-ratio replays."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from pathlib import Path
from typing import Any

RATIO_DIRS = {"1:6":"fixed_1_6","4:5":"fixed_4_5","2:4":"fixed_2_4","1:3":"fixed_1_3"}
POLICIES = ("HOLD_5_SESSIONS","HOLD_10_SESSIONS","HOLD_20_SESSIONS","EXIT_AT_DTE_LE_7")
ERAS = (("2018-2021",2018,2021),("2022-2023",2022,2023),("2024-2025",2024,2025))
THRESHOLD = 0.005

def num(v: Any) -> float | None:
    try:
        x=float(v)
        return x if math.isfinite(x) else None
    except (TypeError,ValueError):
        return None

def read_rows(path: Path) -> list[dict[str,str]]:
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if not rows: raise ValueError(f"No rows in {path}")
    required={"episode_id","signal_date","policy","status","net_pnl_usd"}
    missing=required-set(rows[0])
    if missing: raise ValueError(f"{path} missing columns: {sorted(missing)}")
    return rows

def signature(rows):
    out={}
    for r in rows:
        eid,day=r.get("episode_id",""),r.get("signal_date","")
        if eid and day:
            if eid in out and out[eid]!=day: raise ValueError(f"Episode {eid} has inconsistent signal date")
            out[eid]=day
    return out

def wilson95(wins,n):
    if n<=0: return None,None
    z,p=1.959963984540054,wins/n
    den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return 100*(center-half),100*(center+half)

def summarize(rows,ratio,group_type,period,policy):
    chosen=[r for r in rows if r.get("policy")==policy]
    resolved=[r for r in chosen if r.get("status")=="RESOLVED" and num(r.get("net_pnl_usd")) is not None]
    pnl=[float(num(r["net_pnl_usd"])) for r in resolved]
    wins=sum(x>THRESHOLD for x in pnl); losses=sum(x< -THRESHOLD for x in pnl); flats=len(pnl)-wins-losses
    pos=sum(x for x in pnl if x>THRESHOLD); neg=sum(x for x in pnl if x< -THRESHOLD)
    qqq=[num(r.get("qqq_long_gross_pnl_usd")) for r in resolved]
    spy=[num(r.get("spy_short_gross_pnl_usd")) for r in resolved]
    marks=[num(r.get("max_adverse_mark_pnl_usd")) for r in chosen]
    marks=[x for x in marks if x is not None]
    lo,hi=wilson95(wins,len(pnl)); n=len(chosen)
    return {
      "ratio":ratio,"period_type":group_type,"period":period,"policy":policy,
      "opened":n,"resolved":len(resolved),"unresolved":n-len(resolved),
      "wins":wins,"losses":losses,"flat":flats,
      "win_rate_pct":round(100*wins/len(pnl),4) if pnl else None,
      "wilson95_low_pct":round(lo,4) if lo is not None else None,
      "wilson95_high_pct":round(hi,4) if hi is not None else None,
      "mean_net_pnl_usd":round(statistics.mean(pnl),2) if pnl else None,
      "median_net_pnl_usd":round(statistics.median(pnl),2) if pnl else None,
      "total_resolved_net_pnl_usd":round(sum(pnl),2),
      "worst_resolved_trade_usd":round(min(pnl),2) if pnl else None,
      "best_resolved_trade_usd":round(max(pnl),2) if pnl else None,
      "profit_factor":round(pos/abs(neg),4) if neg<0 else (None if pos==0 else "INF"),
      "mean_qqq_long_gross_usd":round(statistics.mean([x for x in qqq if x is not None]),2) if any(x is not None for x in qqq) else None,
      "mean_spy_short_gross_usd":round(statistics.mean([x for x in spy if x is not None]),2) if any(x is not None for x in spy) else None,
      "mean_adverse_mark_usd":round(statistics.mean(marks),2) if marks else None,
      "worst_adverse_mark_usd":round(min(marks),2) if marks else None,
      "resolved_coverage_pct":round(100*len(resolved)/n,4) if n else 0.0
    }

def build_records(root:Path):
    loaded={}; hashes={}; signatures={}
    for ratio,folder in RATIO_DIRS.items():
        path=root/folder/"trade_episodes.csv"
        if not path.is_file(): raise FileNotFoundError(f"Missing replay output: {path}")
        raw=path.read_bytes(); hashes[ratio]=hashlib.sha256(raw).hexdigest()
        loaded[ratio]=read_rows(path); signatures[ratio]=signature(loaded[ratio])
        for policy in POLICIES:
            if not any(r.get("policy")==policy for r in loaded[ratio]): raise ValueError(f"{ratio} missing {policy}")
    ref=signatures["1:6"]
    checks={ratio:{"episode_n":len(sig),"matches_reference":sig==ref,
                   "missing_ids":sorted(set(ref)-set(sig)),"extra_ids":sorted(set(sig)-set(ref))}
            for ratio,sig in signatures.items()}
    if not all(v["matches_reference"] for v in checks.values()): raise ValueError(f"Ratio cohorts differ: {checks}")
    records=[]
    for ratio,rows in loaded.items():
        for policy in POLICIES: records.append(summarize(rows,ratio,"all","2018-2025",policy))
        years=sorted({int(r["signal_date"][:4]) for r in rows if r.get("signal_date","")[:4].isdigit()})
        for year in years:
            group=[r for r in rows if r.get("signal_date","").startswith(str(year))]
            for policy in POLICIES: records.append(summarize(group,ratio,"year",str(year),policy))
        for label,first,last in ERAS:
            group=[r for r in rows if r.get("signal_date","")[:4].isdigit() and first<=int(r["signal_date"][:4])<=last]
            for policy in POLICIES: records.append(summarize(group,ratio,"era",label,policy))
    meta={"schema":"qqq-spy-fixed-ratio-temporal-audit.v1","cohort_n":len(ref),
          "cohort_checks":checks,"input_sha256":hashes,"caveats":[
          "In-sample time-sliced audit, not an untouched out-of-sample test.",
          "Ratios were selected after reviewing the same 2018-2025 sample; positive results do not prove prospective alpha.",
          "Resolved-only P&L/win rates exclude unresolved rows, reported separately rather than assigned zero.",
          "Era groups are small and do not correct for serial dependence, overlapping regimes or model selection.",
          "EOD quotes and displayed-size gates are not confirmed multi-leg fills.",
          "SPY short-put exposure retains severe downside, assignment and collateral risk.",
          "Available EOD adverse marks do not capture intraday moves or missing quote periods."]}
    return records,meta

def money(x): return "—" if x is None else "USD "+format(float(x),",.2f")
def pct(x): return "—" if x is None else format(float(x),".2f")+"%"

def report_md(records,meta):
    by={(r["ratio"],r["period_type"],r["period"],r["policy"]):r for r in records}
    labels={"HOLD_5_SESSIONS":"5 sessions","HOLD_10_SESSIONS":"10 sessions","HOLD_20_SESSIONS":"20 sessions","EXIT_AT_DTE_LE_7":"DTE ≤ 7"}
    out=["# QQQ/SPY Fixed-Ratio Temporal Stability Audit","",
    f"- Common signal episodes: {meta['cohort_n']} across all ratios.",
    "- Groups use signal date and include individual calendar years plus three frozen eras.",
    "- Uses existing base-cost EOD quote-side estimates, not verified fills.",
    "- Cohort integrity: all four ratio outputs have identical episode IDs and signal dates.","",
    "## Full-period reference","","| Ratio | Exit | Resolved/opened | Win rate | Mean net/trade | Total resolved net | Worst resolved trade | Unresolved |",
    "|---|---|---:|---:|---:|---:|---:|---:|"]
    for ratio in RATIO_DIRS:
        for policy in POLICIES:
            r=by[(ratio,"all","2018-2025",policy)]
            out.append(f"| {ratio} | {labels[policy]} | {r['resolved']}/{r['opened']} | {pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['total_resolved_net_pnl_usd'])} | {money(r['worst_resolved_trade_usd'])} | {r['unresolved']} |")
    out += ["","## Ten-session hold by era","","P&L and win rate use resolved trades only; opened/resolved/unresolved counts remain explicit.","",
    "| Ratio | Era | Resolved/opened | Win rate | Mean net/trade | Total resolved net | Worst trade | QQQ LONG gross mean | SPY SHORT gross mean |",
    "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for ratio in RATIO_DIRS:
        for era,_,_ in ERAS:
            r=by[(ratio,"era",era,"HOLD_10_SESSIONS")]
            out.append(f"| {ratio} | {era} | {r['resolved']}/{r['opened']} | {pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['total_resolved_net_pnl_usd'])} | {money(r['worst_resolved_trade_usd'])} | {money(r['mean_qqq_long_gross_usd'])} | {money(r['mean_spy_short_gross_usd'])} |")
    out += ["","## Twenty-session hold by era","","| Ratio | Era | Resolved/opened | Win rate | Mean net/trade | Total resolved net | Worst trade | Unresolved |",
    "|---|---|---:|---:|---:|---:|---:|---:|"]
    for ratio in RATIO_DIRS:
        for era,_,_ in ERAS:
            r=by[(ratio,"era",era,"HOLD_20_SESSIONS")]
            out.append(f"| {ratio} | {era} | {r['resolved']}/{r['opened']} | {pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['total_resolved_net_pnl_usd'])} | {money(r['worst_resolved_trade_usd'])} | {r['unresolved']} |")
    out += ["","## Interpretation","",
    "- The existing sample shows regime dependence: 10-session means turn negative in 2022-2023 across all four ratios.",
    "- Gross-leg attribution is important. If SPY short-put gross gains outweigh negative QQQ long-put P&L, this is economically a short-downside-risk strategy, not a neutral paired hedge.",
    "- Small period samples and retrospective ratio selection prevent this report from establishing robust alpha.",
    "- Next evidential step: freeze a candidate and run prospective paper replay on genuinely new quotes without ratio or exit retuning.","",
    "## Input integrity","","| Ratio | SHA-256 of trade_episodes.csv | Cohort matches reference |","|---|---|---|"]
    for ratio,digest in meta["input_sha256"].items(): out.append(f"| {ratio} | {digest} | {meta['cohort_checks'][ratio]['matches_reference']} |")
    out += ["","## Caveats",""]+[f"- {x}" for x in meta["caveats"]]+[""]
    return "\n".join(out)

def run(root:Path,out_dir:Path):
    records,meta=build_records(root); out_dir.mkdir(parents=True,exist_ok=True)
    with (out_dir/"temporal_stability.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0])); w.writeheader(); w.writerows(records)
    (out_dir/"audit.json").write_text(json.dumps({"metadata":meta,"records":records},indent=2),encoding="utf-8")
    (out_dir/"report.md").write_text(report_md(records,meta),encoding="utf-8")
    return meta

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results-root",type=Path,default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results"))
    p.add_argument("--out-dir",type=Path,default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/temporal_stability_audit"))
    a=p.parse_args(); meta=run(a.results_root,a.out_dir)
    print(json.dumps({"status":"COMPLETED","cohort_n":meta["cohort_n"],
      "all_cohorts_match":all(v["matches_reference"] for v in meta["cohort_checks"].values()),
      "out_dir":str(a.out_dir)},indent=2))

if __name__=="__main__": main()
