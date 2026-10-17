#!/usr/bin/env python3
"""Combine identical QQQ event-driven portfolio replays at several initial NAVs."""
from __future__ import annotations
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path
from typing import Any

NAVS=(80000,100000,1000000)
SOURCE_END="2025-12-15"


def read_csv(path:Path)->list[dict[str,str]]:
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))


def n(row:dict[str,Any],key:str)->float|None:
    try:
        v=float(row.get(key,""))
        return v if math.isfinite(v) else None
    except (TypeError,ValueError):
        return None


def compare_to_core(row:dict[str,Any],core:dict[str,Any])->dict[str,Any]:
    out=dict(row)
    for field,out_key in (
        ("final_nav_usd","delta_final_nav_usd"),
        ("cagr_pct","delta_cagr_pp"),
        ("maxdd_observed_quote_side_marks_pct","delta_maxdd_pp"),
        ("worst_observed_calendar_year_pct","delta_worst_year_pp"),
    ):
        a,b=n(row,field),n(core,field)
        out[out_key]=round(a-b,6) if a is not None and b is not None else None
    return out


def source_fingerprint(value: Any) -> Any:
    """Compare source identity, not transient download/cache verification status."""
    if isinstance(value, dict):
        return {key: source_fingerprint(item) for key, item in value.items() if key != "status"}
    if isinstance(value, list):
        return [source_fingerprint(item) for item in value]
    return value


def validate_manifests(manifests:dict[int,dict[str,Any]])->dict[str,Any]:
    if set(manifests)!=set(NAVS):
        raise ValueError(f"Expected NAV cases {NAVS}, got {sorted(manifests)}")
    reference=manifests[NAVS[0]]
    for nav,m in manifests.items():
        if abs(float(m.get("initial_nav_usd",0))-nav)>0.01:
            raise ValueError(f"NAV manifest mismatch for {nav}: {m.get('initial_nav_usd')}")
        if m.get("source_window")!=reference.get("source_window"):
            raise ValueError("Source date window mismatch across NAV cases")
        if m.get("source_sessions")!=reference.get("source_sessions") or m.get("signal_count")!=reference.get("signal_count"):
            raise ValueError("Source sessions/signals mismatch across NAV cases")
        if m.get("source_option_terminal_date")!=SOURCE_END:
            raise ValueError("Unexpected option source end date")
        if source_fingerprint(m.get("options_source_files"))!=source_fingerprint(reference.get("options_source_files")):
            raise ValueError("Pinned annual option content signatures differ across NAV cases")
        if source_fingerprint(m.get("underlying_and_repo_source_integrity"))!=source_fingerprint(reference.get("underlying_and_repo_source_integrity")):
            raise ValueError("Underlying/repo source content signatures differ across NAV cases")
        err=float(m.get("max_abs_nav_reconciliation_error_usd",math.inf))
        if not math.isfinite(err) or err>=0.01:
            raise ValueError(f"NAV reconciliation failed for {nav}: {err}")
    return reference


def write_csv(path:Path,rows:list[dict[str,Any]])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("status\nNO_ROWS\n",encoding="utf-8")
        return
    fields=list(dict.fromkeys(k for row in rows for k in row.keys()))
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader();w.writerows(rows)


def run(input_root:Path,out_dir:Path)->dict[str,Any]:
    manifests={};all_rows=[];cores={}
    for nav in NAVS:
        folder=input_root/str(nav)
        if not (folder/"manifest.json").is_file() or not (folder/"summary.csv").is_file():
            raise FileNotFoundError(f"Missing replay output for NAV {nav}: {folder}")
        manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
        rows=read_csv(folder/"summary.csv")
        if len(rows)!=43:
            raise ValueError(f"NAV {nav}: expected 43 account rows, got {len(rows)}")
        if any(abs(float(r.get("initial_nav_usd") or 0)-nav)>0.01 for r in rows):
            raise ValueError(f"NAV {nav}: summary contains another initial NAV")
        core_rows=[r for r in rows if r.get("strategy_id")=="CORE_ONLY"]
        if len(core_rows)!=1:
            raise ValueError(f"NAV {nav}: expected exactly one CORE_ONLY account")
        cores[nav]=core_rows[0];manifests[nav]=manifest
        for r in rows:
            enriched=compare_to_core(r,core_rows[0])
            enriched["nav_case_usd"]=nav
            all_rows.append(enriched)
    ref=validate_manifests(manifests)
    if len(all_rows)!=129:
        raise ValueError(f"Expected 129 account comparisons, got {len(all_rows)}")
    scale_groups=defaultdict(list)
    for row in all_rows:
        if row.get("strategy_id")=="CORE_ONLY":continue
        key=(row["strategy_id"],str(row.get("risk_fraction","")),row.get("cost_case",""))
        scale_groups[key].append(row)
    nonlinear=[]
    for (strategy,risk,cost),rows in sorted(scale_groups.items()):
        rows=sorted(rows,key=lambda r:int(r["nav_case_usd"]))
        if len(rows)!=3:raise ValueError(f"Incomplete NAV triplet for {(strategy,risk,cost)}")
        cagr=[n(r,"cagr_pct") for r in rows];dd=[n(r,"maxdd_observed_quote_side_marks_pct") for r in rows]
        deltas=[n(r,"delta_final_nav_usd") for r in rows]
        nonlinear.append({
          "strategy_id":strategy,"risk_fraction":risk,"cost_case":cost,
          "navs_tested":",".join(str(r["nav_case_usd"]) for r in rows),
          "entries_by_nav":",".join(str(r.get("entries")) for r in rows),
          "blocked_entries_by_nav":",".join(str(r.get("blocked_entries")) for r in rows),
          "final_nav_delta_vs_core_by_nav":",".join("" if v is None else str(round(v,2)) for v in deltas),
          "cagr_min_pct":min(v for v in cagr if v is not None) if any(v is not None for v in cagr) else None,
          "cagr_max_pct":max(v for v in cagr if v is not None) if any(v is not None for v in cagr) else None,
          "observed_maxdd_min_pct":min(v for v in dd if v is not None) if any(v is not None for v in dd) else None,
          "observed_maxdd_max_pct":max(v for v in dd if v is not None) if any(v is not None for v in dd) else None,
          "interpretation":"Entry counts can change nonlinearly when integer risk, quote depth or cash reserve binds.",
        })
    out_dir.mkdir(parents=True,exist_ok=True)
    write_csv(out_dir/"scale_summary.csv",all_rows)
    write_csv(out_dir/"nav_scaling_nonlinearity.csv",nonlinear)
    manifest={
      "research_id":"QQQ_OPTION_PORTFOLIO_NAV_SCALE_REPLAY_V1","navs_tested":list(NAVS),
      "accounts_per_nav":43,"combined_account_rows":len(all_rows),
      "source_window":ref["source_window"],"source_sessions":ref["source_sessions"],
      "signal_count":ref["signal_count"],"source_option_terminal_date":SOURCE_END,
      "options_source_files":ref["options_source_files"],
      "underlying_and_repo_source_integrity":ref["underlying_and_repo_source_integrity"],
      "max_abs_nav_reconciliation_error_usd":max(float(m["max_abs_nav_reconciliation_error_usd"]) for m in manifests.values()),
      "evidence_class":"OBSERVED_EOD_QUOTES_WITH_DERIVED_SIDE_PRICE_EXECUTION_MODEL_NOT_CONFIRMED_FILLS",
      "limitations":[
        "NAV cases share the same 28-event exploratory signal cohort and are not independent strategy trials.",
        "Option history ends 2025-12-15; no 2026 option P&L is inferred.",
        "Observed marks can understate drawdown when quotes are absent.",
        "Terminal payoff budgeting is not broker margin or a bound on interim liquidation loss.",
        "QQQ core is fixed-share, raw-price only, with no dividends or rebalancing.",
        "Scaling tests capacity only; they do not validate a virgin holdout or authorize deployment."
      ]
    }
    (out_dir/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    (out_dir/"REPORT.md").write_text(render_report(manifest,all_rows,nonlinear),encoding="utf-8")
    return manifest


def render_report(manifest,rows,nonlinear):
    lines=[
      "# QQQ Event-Driven Portfolio NAV Scale Replay V1","",
      "**Research-only. No live HUB change and no broker orders.**","",
      "- Initial NAV cases: "+", ".join("USD "+format(v,",") for v in NAVS)+".",
      f"- Same source window: {manifest['source_window'][0]} to {manifest['source_window'][-1]}; {manifest['source_sessions']} sessions; {manifest['signal_count']} fixed events.",
      f"- 129 account rows; maximum NAV reconciliation error USD {manifest['max_abs_nav_reconciliation_error_usd']:.8f}.",
      "- The sole changed input is NAV. Strategy definitions, signals, option selection, holding horizon and costs stay fixed.",
      "- Quote evidence is historical EOD with modeled side-price execution, not confirmed fills. Option history ends 2025-12-15.","",
      "## Core-only baseline by NAV","",
      "| Initial NAV USD | Final NAV USD | CAGR % | Observed MaxDD % | Worst observed year % |","|---:|---:|---:|---:|---:|"
    ]
    for nav in NAVS:
      core=next(r for r in rows if int(r["nav_case_usd"])==nav and r["strategy_id"]=="CORE_ONLY")
      lines.append(f"| {nav:,} | {float(core['final_nav_usd']):,.2f} | {core['cagr_pct']} | {core['maxdd_observed_quote_side_marks_pct']} | {core['worst_observed_calendar_year_pct']} |")
    lines += ["","## Candidate comparison — 1% tail budget, BASE costs","",
      "| NAV USD | Strategy | Final NAV | Delta final vs core | CAGR % | Delta CAGR pp | Observed MaxDD % | Delta MaxDD pp | Entries / blocked | Incomplete marks |",
      "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for nav in NAVS:
      for r in rows:
        if int(r["nav_case_usd"])!=nav or r["strategy_id"]=="CORE_ONLY":continue
        if str(r.get("risk_fraction",""))!="0.01" or r.get("cost_case")!="BASE":continue
        lines.append(f"| {nav:,} | {r['strategy_id']} | {float(r['final_nav_usd']):,.2f} | {float(r['delta_final_nav_usd']):,.2f} | {r['cagr_pct']} | {r['delta_cagr_pp']} | {r['maxdd_observed_quote_side_marks_pct']} | {r['delta_maxdd_pp']} | {r.get('entries')} / {r.get('blocked_entries')} | {r.get('missing_or_incomplete_nav_marks')} |")
    lines += ["","## Capacity nonlinearity","",
      "The full CSV contains all 129 NAV accounts. The following companion view shows how entries and blocked entries changed as initial capital changed; this distinguishes percentage scaling from actual whole-contract feasibility.","",
      "| Strategy | Budget | Costs | Entries at USD 80k / 100k / 1m | Blocked at USD 80k / 100k / 1m | Delta final NAV vs core in USD 80k / 100k / 1m |",
      "|---|---:|---|---|---|---|"]
    for r in nonlinear:
      if r["cost_case"]!="BASE" or str(r["risk_fraction"])!="0.01":continue
      lines.append(f"| {r['strategy_id']} | {float(r['risk_fraction'])*100:.1f}% | {r['cost_case']} | {r['entries_by_nav']} | {r['blocked_entries_by_nav']} | {r['final_nav_delta_vs_core_by_nav']} |")
    lines += ["","## Interpretation limits","",
      "- Compare each option account only with CORE_ONLY at the same starting NAV; raw ending balances across different NAVs are not a strategy ranking.",
      "- A larger NAV can unlock a whole contract, while displayed quote size can cap positions; therefore entries, costs and returns need not scale linearly.",
      "- An option account whose entries are all blocked is effectively the core baseline, not evidence of added value.",
      "- These three NAV levels are checkpoints, not a claim that every intermediate NAV was tested.",
      "- Missing quote marks are never forward-filled. MaxDD may understate losses; broker margin, assignment, early exercise, forced liquidation and multi-leg sequencing are not modeled.",
      "- All three NAV cases share the same exploratory 28-signal cohort; this is not out-of-sample confirmation.",""]
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser();p.add_argument("--input-root",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();m=run(a.input_root,a.out);print(json.dumps(m,indent=2));print((a.out/"REPORT.md").read_text(encoding="utf-8"))


if __name__=="__main__":main()
