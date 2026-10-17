#!/usr/bin/env python3
"""Cost/time-split/tail-capacity audit of a locked QQQ options event replay."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUN = "run-39003581461-d2e3d21c54c1e02a11c75218abc588458b59b4d1"
TRADES_REL = Path("research/qqq_option_shortlist_results_v1") / SOURCE_RUN / "trades.csv"
SIGNALS_REL = Path("research/qqq_option_shortlist_results_v1") / SOURCE_RUN / "signals.csv"
EXPECTED_TRADES_GIT_BLOB_SHA = "ba5fc1fa0fabf8cd914735503905cac6ee1f631e"
NAV_USD, MULTIPLIER, BASE_SLIPPAGE_PER_SHARE, STRESS_SLIPPAGE_PER_SHARE, COMMISSION = 80000.0, 100, 0.05, 0.10, 0.65
BUDGETS = (0.005, 0.01, 0.02)
Z95 = 1.959963984540054
STRATEGIES = ("CALL_DEBIT_50D_10D","CALL_DEBIT_PLUS_LONG_PUT_10D",
 "PUT_SHORT_HEAVY_1x1","PUT_SHORT_HEAVY_1x2","PUT_SHORT_HEAVY_1x3","PUT_SHORT_HEAVY_1x4",
 "PUT_SHORT_HEAVY_1x5","PUT_SHORT_HEAVY_1x6","PUT_LONG_HEAVY_1x1","PUT_LONG_HEAVY_2x1",
 "PUT_LONG_HEAVY_3x1","PUT_LONG_HEAVY_4x1","PUT_LONG_HEAVY_5x1","PUT_LONG_HEAVY_6x1")
PERIODS = (("FULL_2018_2025",2018,2025),("EARLIER_2018_2022",2018,2022),
 ("LATER_2023_2025_EXPLORATORY",2023,2025))


def fnum(v: Any):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except (TypeError,ValueError): return None


def git_blob_sha_bytes(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii")+data).hexdigest()


def read_csv(path: Path):
    with path.open("r",encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))


def legs(row):
    raw=row.get("contract_legs")
    xs=raw if isinstance(raw,list) else json.loads(str(raw or "[]"))
    if not xs or not isinstance(xs,list): raise ValueError(f"Missing legs: {row.get('signal_date')}")
    if any(not isinstance(x,dict) or int(x.get("qty",0))<1 for x in xs): raise ValueError("Bad leg quantity")
    return xs


def ncontracts(row): return sum(int(x["qty"]) for x in legs(row))


def pnl_cost(base_pnl: float, n: int, case: str) -> float:
    if case=="ZERO_FRICTION": return base_pnl+n*(2*BASE_SLIPPAGE_PER_SHARE*MULTIPLIER+2*COMMISSION)
    if case=="BASE": return base_pnl
    if case=="STRESS": return base_pnl-n*2*(STRESS_SLIPPAGE_PER_SHARE-BASE_SLIPPAGE_PER_SHARE)*MULTIPLIER
    raise ValueError(case)


def terminal_loss_cost(base_loss: float, n: int, case: str) -> float:
    if case=="ZERO_FRICTION": return max(0.0,base_loss-n*(BASE_SLIPPAGE_PER_SHARE*MULTIPLIER+COMMISSION))
    if case=="BASE": return max(0.0,base_loss)
    if case=="STRESS": return max(0.0,base_loss+n*(STRESS_SLIPPAGE_PER_SHARE-BASE_SLIPPAGE_PER_SHARE)*MULTIPLIER)
    raise ValueError(case)


def risk_units(nav: float,budget: float,loss: float,depth: int) -> int:
    return 0 if depth<=0 else (depth if loss<=0 else min(depth,max(0,math.floor(nav*budget/loss))))


def wilson(wins:int,n:int):
    if n<=0:return None,None
    p=wins/n; z=Z95; den=1+z*z/n
    c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0,c-h),min(1,c+h)


def norm(r):
    y=None
    try:y=int(str(r.get("signal_date",""))[:4])
    except ValueError:pass
    return {**r,"_status":str(r.get("status","")),"_strategy":str(r.get("strategy_id","")),
      "_date":str(r.get("signal_date","")),"_year":y,"_legs":legs(r),
      "_n":ncontracts(r),"_pnl":fnum(r.get("net_pnl_usd")),"_loss":fnum(r.get("terminal_worst_loss_usd")),
      "_depth":int(fnum(r.get("depth_units_at_entry")) or 0),"_mae":fnum(r.get("mae_one_unit_usd"))}


def summarize(rows,case):
    resolved=[r for r in rows if r["_status"]=="RESOLVED" and r["_pnl"] is not None]
    ps=[pnl_cost(float(r["_pnl"]),r["_n"],case) for r in resolved]
    wins=sum(x>0 for x in ps); lo,hi=wilson(wins,len(ps))
    gain=sum(x for x in ps if x>0); loss=-sum(x for x in ps if x<0)
    def feasible(b):
        return sum(risk_units(NAV_USD,b,terminal_loss_cost(float(r["_loss"] or 0),r["_n"],case),r["_depth"])>0 for r in resolved)
    mae=[r["_mae"] for r in resolved if r["_mae"] is not None]
    return {"recorded_episodes":len(rows),"resolved":len(ps),"unresolved":sum(r["_status"]!="RESOLVED" for r in rows),
      "wins":wins,"win_rate_pct":round(100*wins/len(ps),4) if ps else None,
      "win_rate_wilson95_low_pct":round(100*lo,4) if lo is not None else None,
      "win_rate_wilson95_high_pct":round(100*hi,4) if hi is not None else None,
      "mean_pnl_usd_per_unit":round(sum(ps)/len(ps),2) if ps else None,
      "median_pnl_usd_per_unit":round(median(ps),2) if ps else None,
      "total_pnl_one_unit_per_episode_usd":round(sum(ps),2) if ps else None,
      "worst_pnl_usd_per_unit":round(min(ps),2) if ps else None,
      "profit_factor":round(gain/loss,5) if loss else (None if not gain else "INF_NO_LOSSES_IN_SAMPLE"),
      "median_terminal_worst_loss_usd":round(median([terminal_loss_cost(float(r["_loss"] or 0),r["_n"],case) for r in resolved]),2) if resolved else None,
      "episodes_sizeable_at_0p5pct_budget":feasible(.005),"episodes_sizeable_at_1pct_budget":feasible(.01),
      "episodes_sizeable_at_2pct_budget":feasible(.02),
      "mean_base_cost_MAE_usd":round(sum(mae)/len(mae),2) if mae else None,
      "interpretation":"one unit per event; not portfolio CAGR/MaxDD or broker-approved capacity"}


def write_csv(path,rows):
    if not rows: path.write_text("status\nNO_ROWS\n",encoding="utf-8"); return
    keys=sorted({k for r in rows for k in r})
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore");w.writeheader();w.writerows(rows)


def paired(trades):
    index={(r["_date"],r["_strategy"]):r for r in trades if r["_status"]=="RESOLVED" and r["_pnl"] is not None}
    detail=[]
    for dt in sorted({d for d,s in index if s in {"CALL_DEBIT_50D_10D","CALL_DEBIT_PLUS_LONG_PUT_10D"}}):
        c=index.get((dt,"CALL_DEBIT_50D_10D"));h=index.get((dt,"CALL_DEBIT_PLUS_LONG_PUT_10D"))
        if c is None or h is None:continue
        row={"signal_date":dt,"year":c["_year"],"call_contract_count":c["_n"],"hedged_contract_count":h["_n"],
             "call_pnl_base_usd":c["_pnl"],"hedged_pnl_base_usd":h["_pnl"],
             "call_mae_base_usd":c["_mae"],"hedged_mae_base_usd":h["_mae"],
             "hedge_mae_less_adverse":h["_mae"] is not None and c["_mae"] is not None and h["_mae"]>c["_mae"]}
        for case in ("ZERO_FRICTION","BASE","STRESS"):
            cv=pnl_cost(float(c["_pnl"]),c["_n"],case);hv=pnl_cost(float(h["_pnl"]),h["_n"],case)
            row[f"call_{case.lower()}_usd"]=round(cv,2);row[f"hedged_{case.lower()}_usd"]=round(hv,2)
            row[f"hedged_minus_call_{case.lower()}_usd"]=round(hv-cv,2)
        detail.append(row)
    summary=[]
    for case in ("ZERO_FRICTION","BASE","STRESS"):
        ds=[r[f"hedged_minus_call_{case.lower()}_usd"] for r in detail]
        mds=[float(r["hedged_mae_base_usd"])-float(r["call_mae_base_usd"]) for r in detail if r["hedged_mae_base_usd"] is not None and r["call_mae_base_usd"] is not None]
        beats=sum(d>0 for d in ds)
        summary.append({"cost_case":case,"paired_events":len(ds),"hedged_higher_PnL_count":beats,
          "hedged_higher_PnL_pct":round(100*beats/len(ds),2) if ds else None,
          "mean_hedged_minus_call_PnL_usd":round(sum(ds)/len(ds),2) if ds else None,
          "median_hedged_minus_call_PnL_usd":round(median(ds),2) if ds else None,
          "events_with_less_adverse_MAE":sum(bool(r["hedge_mae_less_adverse"]) for r in detail),
          "mean_MAE_delta_hedged_minus_call_usd_base_cost":round(sum(mds)/len(mds),2) if mds else None,
          "warning":"paired historical episodes; does not establish a causal hedge benefit"})
    return detail,summary


def run(source:Path,out:Path):
    payload=source.read_bytes();blob=git_blob_sha_bytes(payload)
    if blob!=EXPECTED_TRADES_GIT_BLOB_SHA:raise ValueError(f"Locked input Git blob SHA mismatch: {blob}")
    raw=read_csv(source)
    if len(raw)!=387:raise ValueError(f"Expected 387 rows, got {len(raw)}")
    trades=[norm(r) for r in raw]
    dates=sorted({r["_date"] for r in trades if r["_date"]})
    if len(dates)!=28:raise ValueError(f"Expected 28 unique signal dates, got {len(dates)}")
    summaries=[]
    for strategy in STRATEGIES:
        sr=[r for r in trades if r["_strategy"]==strategy]
        for period,y0,y1 in PERIODS:
            pr=[r for r in sr if r["_year"] is not None and y0<=r["_year"]<=y1]
            for case in ("ZERO_FRICTION","BASE","STRESS"):
                summaries.append({"strategy_id":strategy,"period":period,"cost_case":case,**summarize(pr,case)})
    hedge_detail,hedge_summary=paired(trades)
    signal_raw=read_csv(ROOT/SIGNALS_REL)
    signal_rows=[]
    for r in signal_raw:
        dt=str(r.get("signal_date",""))
        try:y=int(dt[:4])
        except ValueError:y=None
        try:nsel=len(json.loads(r.get("candidates") or "[]"))
        except (ValueError,TypeError):nsel=0
        signal_rows.append({"signal_date":dt,"year":y,"status":r.get("status"),"spot":r.get("spot"),"selected_candidates":nsel})
    out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"cost_time_split_summary.csv",summaries)
    write_csv(out/"paired_call_hedge_events.csv",hedge_detail)
    write_csv(out/"paired_call_hedge_summary.csv",hedge_summary)
    write_csv(out/"signal_audit.csv",signal_rows)
    manifest={"research_id":"QQQ_OPTION_SHORTLIST_VALIDATION_V1","source_run_id":39003581461,
      "source_sha":"d2e3d21c54c1e02a11c75218abc588458b59b4d1","input_trades_git_blob_sha1":blob,
      "unique_signal_dates":len(dates),"input_rows":len(raw),"resolved_rows":sum(r["_status"]=="RESOLVED" for r in trades),
      "nav_reference_usd":NAV_USD,"source_option_end":"2025-12-15",
      "cost_cases":{"ZERO_FRICTION":"BASE P&L + $11.30 per option contract","BASE":"$0.05/share/leg/side slippage plus $0.65/contract/side commission","STRESS":"BASE P&L - $10 per option contract for doubled slippage"},
      "time_split":"2023-2025 already inspected; descriptive only, not virgin holdout",
      "evidence_class":"OBSERVED_EOD_QUOTES_WITH_DERIVED_QUOTE_SIDE_REPLAY_NOT_CONFIRMED_FILLS"}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    (out/"REPORT.md").write_text(render(manifest,summaries,hedge_summary),encoding="utf-8")
    return manifest


def render(manifest,summaries,hedges):
    ix={(r["strategy_id"],r["period"],r["cost_case"]):r for r in summaries}
    lines=["# QQQ Option Shortlist Validation V1","",
      "Evidence: observed historical EOD quotes with derived quote-side replay; not confirmed fills.","",
      "## Locked cohort","",
      f"- Source run: {manifest['source_run_id']}; locked trade input Git blob SHA-1: {manifest['input_trades_git_blob_sha1']}.",
      f"- Unique signal dates: {manifest['unique_signal_dates']}; recorded event/strategy rows: {manifest['input_rows']}; resolved rows: {manifest['resolved_rows']}.",
      "- Option chain ends 2025-12-15. The later 2023-2025 split has already been inspected and is not a virgin holdout.","",
      "## Full-period BASE results and 95% Wilson uncertainty","",
      "| Strategy | N | Win % (95% Wilson interval) | Mean P&L/unit | PF | Worst P&L | 1% NAV-tail-budget-sizeable episodes |",
      "|---|---:|---:|---:|---:|---:|---:|"]
    chosen=("CALL_DEBIT_50D_10D","CALL_DEBIT_PLUS_LONG_PUT_10D","PUT_SHORT_HEAVY_1x4","PUT_SHORT_HEAVY_1x5","PUT_SHORT_HEAVY_1x6","PUT_LONG_HEAVY_1x1","PUT_LONG_HEAVY_2x1")
    for s in chosen:
        r=ix[(s,"FULL_2018_2025","BASE")]
        ci="—" if r["win_rate_wilson95_low_pct"] is None else f"{r['win_rate_wilson95_low_pct']:.1f}–{r['win_rate_wilson95_high_pct']:.1f}%"
        lines.append(f"| {s} | {r['resolved']} | {r['win_rate_pct']}% ({ci}) | {r['mean_pnl_usd_per_unit']} | {r['profit_factor']} | {r['worst_pnl_usd_per_unit']} | {r['episodes_sizeable_at_1pct_budget']} |")
    lines += ["","## Paired call debit versus call debit plus long put","",
      "| Cost case | Matched events | Hedge higher P&L | Mean hedge-minus-call | Median difference | Events with less-adverse MAE | Mean MAE delta |",
      "|---|---:|---:|---:|---:|---:|---:|"]
    for r in hedges:
        lines.append(f"| {r['cost_case']} | {r['paired_events']} | {r['hedged_higher_PnL_count']} ({r['hedged_higher_PnL_pct']}%) | {r['mean_hedged_minus_call_PnL_usd']} | {r['median_hedged_minus_call_PnL_usd']} | {r['events_with_less_adverse_MAE']} | {r['mean_MAE_delta_hedged_minus_call_usd_base_cost']} |")
    lines += ["","## Interpretation","",
      "- The CALL debit vertical is a candidate for further research only: positive event-average P&L is not a compounded return, and only a minority of entries fit the 1% NAV terminal-loss budget under the existing observed entry-side sizing.",
      "- The added long put did not improve matched P&L consistently; do not include it by default. Its MAE improvement was mixed rather than universal.",
      "- PUT short-heavy 1:5 and 1:6 have high single-unit win rates in this small cohort, but their QQQ=0 terminal losses leave zero whole units inside the 0.5%, 1%, and 2% NAV tail budgets for the recorded entries. The apparent expectancy is therefore not deployable under the stated tail budget.",
      "- Long-heavy PUT ratios were net negative in this selected reversal cohort.",
      "- The cost/time split is descriptive; 9 later-period events are too few to confirm persistence, and this period has already been inspected.",
      "- Episode win rates and sums are one unit per event—not portfolio CAGR/MaxDD. Historical EOD marks are not authenticated fills; margin, assignment, intraday liquidation and multi-leg execution sequencing remain unmodelled.","",
      "## Next boundary","",
      "- Freeze the signal and candidate-selection rules. Do not tune the 2.1% threshold using these same results.",
      "- A genuine confirmatory step needs timestamped quote captures after 2025-12-15, logged before the subsequent marks occur. If no freely accessible archival source exists, collect prospective paper data rather than substituting modeled option prices.",
      "- No live HUB policy or broker-order path is modified by this validation.",""]
    return "\n".join(lines)


def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,default=ROOT/TRADES_REL)
    p.add_argument("--out",type=Path,default=ROOT/"research/qqq_option_shortlist_validation_v1/results")
    a=p.parse_args();m=run(a.source,a.out);print(json.dumps(m,indent=2));print((a.out/"REPORT.md").read_text())


if __name__=="__main__":main()
